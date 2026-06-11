import sys
import h5py

def verify_h5ad(path):
    """Verify h5ad file can be fully read including obs/var."""
    try:
        with h5py.File(path, 'r') as f:
            # Basic structure
            keys = list(f.keys())
            print(f"Root keys: {keys}")

            # Check obs
            if 'obs' in f:
                obs_keys = list(f['obs'].keys())
                print(f"obs keys ({len(obs_keys)}): {obs_keys[:10]}...")
            else:
                print("WARNING: no 'obs' group")
                return False

            # Check var
            if 'var' in f:
                var_keys = list(f['var'].keys())
                print(f"var keys ({len(var_keys)}): {var_keys[:10]}...")
            else:
                print("WARNING: no 'var' group")
                return False

            # Check X
            if 'X' in f:
                shape = f['X'].shape
                print(f"X shape: {shape}")
            else:
                print("WARNING: no 'X' dataset")
                return False

            # Try reading last 1MB of file to check for zero padding
            import os
            size = os.path.getsize(path)
            with open(path, 'rb') as raw:
                raw.seek(size - 1024*1024)
                last_mb = raw.read(1024*1024)
                nonzero = sum(1 for b in last_mb if b != 0)
                print(f"Last 1MB non-zero bytes: {nonzero} / {len(last_mb)}")
                if nonzero == 0:
                    print("CRITICAL: Last 1MB is all zeros - file is truncated/corrupted!")
                    return False

        print("VERIFICATION PASSED")
        return True
    except Exception as e:
        print(f"VERIFICATION FAILED: {e}")
        return False

if __name__ == '__main__':
    path = sys.argv[1]
    ok = verify_h5ad(path)
    sys.exit(0 if ok else 1)
