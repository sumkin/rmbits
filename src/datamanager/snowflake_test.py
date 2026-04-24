import yaml


import snowflake.connector 


if __name__ == "__main__":
    with open("/home/ay49514/rmbits/config.yaml") as f:
        d = yaml.load(f)
        ctx = snowflake.connector.connect(
            user=d['SNOWFLAKE_DATABASE']['USER'],
            private_key_file=d['SNOWFLAKE_DATABASE']['PRIVATE_KEY_FILE'],
            private_key_file_pwd=d['SNOWFLAKE_DATABASE']['PRIVATE_KEY_FILE_PWD'],
            account=d['SNOWFLAKE_DATABASE']['ACCOUNT']
        )
        cur = ctx.cursor()
        cur.execute("SHOW COLUMNS IN TABLE AYDP_PROD.PUBLISH_RMP.F_NRM_BIF_LEG_CURRENT")
        for i in range(100):
            row = cur.fetchone()
            print(i + 1, row[2], row[3])



