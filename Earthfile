# Earthfile
VERSION 0.6
FROM python:3.10-slim

deps:
    RUN pip install wheel
    COPY requirements.txt ./
    RUN pip wheel -r requirements.txt --wheel-dir=wheels
    SAVE ARTIFACT wheels /wheels

docker:
    RUN apt-get update && apt-get install -y libgdal28
    COPY github.com/allixender/DGGRID+build/dggrid /usr/local/bin/dggrid
    COPY github.com/allixender/dggrid4py+build/dggrid4py-0.2.6-py3-none-any.whl dggrid4py-0.2.6-py3-none-any.whl
    COPY +deps/wheels wheels
    COPY requirements.txt ./
    RUN pip install --no-index --find-links=wheels -r requirements.txt
    RUN pip install dggrid4py-0.2.6-py3-none-any.whl
    WORKDIR /webapi
    COPY webapi /webapi
    RUN mv /webapi/.env.example /webapi/.env
    ENTRYPOINT ["uvicorn", "main:create_app", "--host", "0.0.0.0", "--proxy-headers", "--port", "80"]
    SAVE IMAGE dggrid-py:ci



    
