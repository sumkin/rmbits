import yaml


import snowflake.connector 


if __name__ == "__main__":
    with open("/home/ay49514/rmbits/config.yaml") as f:
        d = yaml.load(f)
        ctx = snowflake.connector.connect(
            account = d['SNOWFLAKE_DATABASE']['ACCOUNT'],
            user = d['SNOWFLAKE_DATABASE']['USER'],
            password = d['SNOWFLAKE_DATABASE']['PASSWORD'],
            schema = d['SNOWFLAKE_DATABASE']['SCHEMA'],
            warehouse = d['SNOWFLAKE_DATABASE']['WAREHOUSE'],
            role = d['SNOWFLAKE_DATABASE']['ROLE']
        )
        cur = ctx.cursor()
        """
        cur.execute("SELECT\
                       GEO_OD_TS_KEY,\
                       BASE_OD_DEPT_DATE,\
                       POC,\
                       BOOKING_CLASS,\
                       SUM(OD_PAX_COUNT),\
                       AVG(YIELD)\
                     FROM RMP_SANDBOX.REPORT.NRM_BKG_CURVE\
                     WHERE DTD = 0\
                     GROUP BY GEO_OD_TS_KEY, BASE_OD_DEPT_DATE, POC, BOOKING_CLASS")
        """
        #cur.execute("SELECT * FROM AYDP_PROD.PUBLISH_RMP.F_NRM_BIF_LEG_CURRENT")
        cur.execute("SHOW COLUMNS IN TABLE AYDP_PROD.PUBLISH_RMP.F_NRM_BIF_LEG_CURRENT")
        for i in range(100):
            row = cur.fetchone()
            print(i + 1, row[2], row[3])



