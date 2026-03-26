import zipfile

for name in ['ModoA_PythonPuro', 'ModoB_Prefect', 'ModoC_Docker']:
    zp = f'dist/{name}_20260325.zip'
    with zipfile.ZipFile(zp) as z:
        files = z.namelist()
        has_leeme = any('LEEME' in f for f in files)
        has_docker = any('Dockerfile' in f or 'docker-compose' in f for f in files)
        has_prefect = any('prefect_pipeline' in f for f in files)
        has_run = any('run_pipeline' in f for f in files)
        has_src = any('src/vfluxx' in f for f in files)
        has_data = any('Datos Termocuplas' in f for f in files)
        has_stages = any('stages/' in f for f in files)
        size_mb = sum(i.file_size for i in z.infolist()) / (1024*1024)
        print(f"\n{name} ({len(files)} archivos, {size_mb:.1f} MB descomprimido):")
        print(f"  LEEME.txt: {has_leeme}")
        print(f"  src/vfluxx: {has_src}")
        print(f"  data: {has_data}")
        print(f"  stages/: {has_stages}")
        print(f"  run_pipeline: {has_run}")
        print(f"  prefect_pipeline: {has_prefect}")
        print(f"  Docker: {has_docker}")
