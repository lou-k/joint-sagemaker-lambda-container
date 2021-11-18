# This is where all of the source code will go.
ARG FUNCTION_DIR="/opt/app/"
ARG PYTHON_VERSION="3.7"

# We'll use a multi-stage build to install the lambda runtime 
# This follows the examples in https://pypi.org/project/awslambdaric/ and https://docs.aws.amazon.com/lambda/latest/dg/images-create.html#images-reqs

#
# -------------- Stage 1: Install function and lambda runtime environment ------------------
#

FROM python:${PYTHON_VERSION}-slim-buster AS builder-image
# Include global arg in this stage of the build
ARG FUNCTION_DIR
# Install aws-lambda-cpp build dependencies
RUN apt-get update && \
  apt-get install -y \
  g++ \
  make \
  cmake \
  unzip \
  libcurl4-openssl-dev \
  build-essential

RUN mkdir -p ${FUNCTION_DIR}

# Install the dependencies from the Pipefile
COPY Pipfile /tmp/
RUN pip install pipenv && \
    cd /tmp && \
    pipenv lock -r > /tmp/requirements.txt && \
    pip install -r /tmp/requirements.txt --target  ${FUNCTION_DIR}

# Install Lambda Runtime Interface Client for Python
# This _could_ have been installed via the Pipfile but we want to be sure.
RUN pip install awslambdaric --target ${FUNCTION_DIR}

#
# -------------- Stage 2: Build the final runtime image ------------------
#

FROM python:${PYTHON_VERSION}-slim-buster
ARG FUNCTION_DIR
# Install runtime requirements like libgomp
RUN apt-get update && \
    apt-get install -y build-essential && \
    rm -rf /var/cache/apt /var/lib/apt/lists
# Set working directory to function root directory
WORKDIR ${FUNCTION_DIR}
# Copy in the built dependencies
COPY --from=builder-image ${FUNCTION_DIR} ${FUNCTION_DIR}
# (Optional) Add Lambda Runtime Interface Emulator and use a script in the ENTRYPOINT for simpler local runs
ADD https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/latest/download/aws-lambda-rie /usr/bin/aws-lambda-rie
# Copy function code
COPY src/* ${FUNCTION_DIR}
# Move the entry script to the root
RUN mv ${FUNCTION_DIR}/entry.sh /
# Set permissions and defaults
RUN chmod 755 /usr/bin/aws-lambda-rie /entry.sh
ENTRYPOINT [ "/entry.sh" ]
CMD [ "lambda.handler" ]