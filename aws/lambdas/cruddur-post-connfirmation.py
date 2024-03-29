import json
import psycopg2
import os

def lambda_handler(event, context):
    user = event['request']['userAttributes']
    print('userAttributes')# for debugging
    print(user)# for debugging

    
    try:
      print('entered-try') # for debugging
      sql = """
         INSERT INTO public.users (
          display_name, 
          email,
          handle, 
          cognito_user_id
          ) 
        VALUES(
            %(user_display_name)s,
            %(user_emails)s,
            %(user_handle)s,
            %(user_cognito_id)s
            )
      """
      print('SQL Statement ----')# for debugging
      print(sql)# for debugging
      conn = psycopg2.connect(os.getenv('CONNECTION_URL'))
      cur = conn.cursor()
      params = {
        'user_display_name' : user['name'],
        'user_emails' : user['email'],
        'user_handle' : user['preferred_username'],
        'cognito_user_id' : user['sub']
      }
      cur.execute(sql, params)
      conn.commit() 

    except (Exception, psycopg2.DatabaseError) as error:
      print(error)
    finally:
      if conn is not None:
          cur.close()
          conn.close()
          print('Database connection closed.')
    return event