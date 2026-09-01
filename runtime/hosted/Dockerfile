FROM public.ecr.aws/lambda/python:3.12
COPY runtime/hosted/requirements.txt ${LAMBDA_TASK_ROOT}/requirements.txt
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt
COPY . ${LAMBDA_TASK_ROOT}/repog
ENV PYTHONPATH=${LAMBDA_TASK_ROOT}/repog
CMD ["runtime.hosted.handler.lambda_handler"]
