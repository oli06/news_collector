FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the project source code from the local host to the filesystem of the container at the working directory.
COPY . .

CMD ["python3", "./run.py"]