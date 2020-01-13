FROM python:3.8-alpine
WORKDIR /app/api
ADD . /app
RUN pip install -r ./requirements.txt
EXPOSE 80
ENV NAME World
CMD ["python","app.py"]