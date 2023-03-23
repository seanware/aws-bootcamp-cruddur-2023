-- this file was manually created
INSERT INTO public.users (display_name, handle, email, cognito_user_id)
VALUES
  
  ('Sean Ware', 'sean', 'seanaware@gmail.com', 'MOCK'),
  ('Jacob Coleson', 'jake', 'alterego4891@mail.com', 'MOCK'),
  ('Citizen Gakar', 'Gakar', 'gakar@narn.com', 'MOCK' );

INSERT INTO public.activities (user_uuid, message, expires_at)
VALUES
  (
    (SELECT uuid from public.users WHERE users.handle = 'sean' LIMIT 1),
    'This was imported as seed data!',
    current_timestamp + interval '10 day'
  )