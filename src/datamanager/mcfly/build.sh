#!/bin/bash

rm mcfly.zip
zip -r mcfly.zip .
aws s3 cp mcfly.zip s3://ay-emr-job/tmp/mcfly.zip


