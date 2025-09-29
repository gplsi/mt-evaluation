
#FROM nvcr.io/nvidia/pytorch:24.02-py3
FROM nvcr.io/nvidia/pytorch:25.05-py3

# Argumentos para UID y GID
ARG USER_ID
ARG GROUP_ID

RUN groupadd -g $GROUP_ID usergroup && \
    useradd -m -u $USER_ID -g usergroup user

COPY . /home/user/app

RUN mkdir -p /home/user/app /home/user/app/evaluaciones /home/user/app/evaluaciones/reports /home/user/app/evaluaciones/results /home/user/app/evaluaciones_gold /home/user/app/evaluaciones_gold/reports /home/user/app/evaluaciones_gold/results /models /home/user/app/outputLogs 


RUN chgrp -R usergroup /home/user/app /home/user/app/evaluaciones /home/user/app/evaluaciones/reports /home/user/app/evaluaciones/results /home/user/app/evaluaciones_gold /home/user/app/evaluaciones_gold/reports /home/user/app/evaluaciones_gold/results /models /home/user/app/outputLogs && \
chmod -R 770 /home/user/app /home/user/app/evaluaciones /home/user/app/evaluaciones/reports /home/user/app/evaluaciones/results /home/user/app/evaluaciones_gold /home/user/app/evaluaciones_gold/reports /home/user/app/evaluaciones_gold/results /models /home/user/app/outputLogs && \
chmod g+s /home/user/app /home/user/app/evaluaciones /home/user/app/evaluaciones/reports /home/user/app/evaluaciones/results /home/user/app/evaluaciones_gold /home/user/app/evaluaciones_gold/reports /home/user/app/evaluaciones_gold/results /models /home/user/app/outputLogs && \
chown -R user:usergroup /home/user/app && chmod -R 770 /home/user/app && \
chown -R user:usergroup /home/user/app/evaluaciones && chmod -R 770 /home/user/app/evaluaciones && \
chown -R user:usergroup /home/user/app/evaluaciones/reports && chmod -R 770 /home/user/app/evaluaciones/reports && \
chown -R user:usergroup /home/user/app/evaluaciones/results && chmod -R 770 /home/user/app/evaluaciones/results && \
chown -R user:usergroup /models && chmod -R 770 /models




WORKDIR /home/user/app
# INSTALL PACKAGES
RUN pip install -e . && \
pip uninstall pydantic -y && \
pip install --no-cache-dir pydantic wandb sentencepiece openpyxl && \
apt-get install --reinstall -y ca-certificates

RUN pip install datasets==3.6.0

#COPY entrypoint.sh /home/user/app/launch_scripts/entrypoint.sh
#RUN chmod +x -R /home/user/app/launch_scripts

#COPY entrypoint.sh /home/user/app/entrypoint.sh
RUN chmod +x /home/user/app/entrypoint.sh
RUN chmod +x -R /home/user/app/launch_scripts
#RUN chmod +x -R /home/user/app
USER user
#WORKDIR /home/user/app/launch_scripts
CMD ["/bin/bash", "./entrypoint.sh"]
#CMD ["/bin/bash"]