# -*- mode: python -*-
# import sys
# sys.setrecursionlimit(5000)
block_cipher = None

#hidden_models=['pywt._extensions._cwt','scipy._lib.messagestream','numpy','scipy._lib.messagestream', 'scipy', 'scipy.signal',
#'scipy.signal.bsplines', 'scipy.special', 'scipy.special._ufuncs_cxx','scipy.linalg.cython_blas','scipy.linalg.cython_lapack',
#'scipy.integrate', 'scipy.integrate.quadrature', 'scipy.integrate.odepack', 'scipy.integrate._odepack', 'scipy.integrate.quadpack',
#'scipy.integrate._quadpack','scipy.integrate._ode', 'scipy.integrate.vode', 'scipy.integrate._dop', 'scipy._lib', 'scipy._build_utils','scipy.__config__',
#'scipy.integrate.lsoda', 'scipy.cluster','scipy.constants','scipy.fftpack','scipy.interpolate','scipy.io','scipy.linalg',
#'scipy.misc','scipy.ndimage','scipy.odr','scipy.optimize','scipy.setup','scipy.sparse','scipy.spatial','scipy.special','scipy.stats','scipy.version'
#]
a = Analysis(['client.py'],
             pathex=['C:\Users\rahul\ChatApp\EncryptionServer'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher
             )
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='ChatAPP',
          debug=True,
          strip=False,
          upx=True,
          console=False )
#coll = COLLECT(exe,
#               a.binaries,
#               a.zipfiles,
#               a.datas,
#               strip=False,
#               upx=True,
#               name='ChatAPP')
