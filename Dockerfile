# Dockerfile

# Get latest 'golang' image from hub.docker.com ; name it as 'builder' to be referenced
FROM python:2.7.16-alpine3.9

# Location is taken using $GOPATH; Full Path '/Users/<user_name>/go/src/<project_name>

# Copy everything from local directory to container directory
# Syntax: COPY ./source ./destination
COPY . ./app
WORKDIR /app

RUN apk update && apk upgrade && \
    apk add --no-cache bash git openssh gcc python-dev musl-dev pcre-dev linux-headers
RUN pip install -r requirements.txt

EXPOSE 5555
# Start the app
CMD ["python","./spike-server.py","init"]
CMD ["python","./spike-server.py","run"]
