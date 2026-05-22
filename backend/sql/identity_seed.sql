-- Seed identity channels for existing authors
insert into public.author_identities (author_id, platform, identity_value, normalized_value, verified, metadata)
select id, 'instagram', '@maya.writes', 'maya.writes', true, '{"source":"onboarding"}'::jsonb
from public.authors where email = 'maya.richardson@bookleaf.ai'
on conflict do nothing;

insert into public.author_identities (author_id, platform, identity_value, normalized_value, verified, metadata)
select id, 'phone', '+1-202-555-0126', '12025550126', true, '{"source":"crm"}'::jsonb
from public.authors where email = 'maya.richardson@bookleaf.ai'
on conflict do nothing;

insert into public.author_identities (author_id, platform, identity_value, normalized_value, verified, metadata)
select id, 'whatsapp', '+1-202-555-0126', '12025550126', true, '{"source":"whatsapp_sync"}'::jsonb
from public.authors where email = 'maya.richardson@bookleaf.ai'
on conflict do nothing;

insert into public.author_identities (author_id, platform, identity_value, normalized_value, verified, metadata)
select id, 'instagram', '@daniel.builds', 'daniel.builds', true, '{"source":"onboarding"}'::jsonb
from public.authors where email = 'daniel.park@bookleaf.ai'
on conflict do nothing;

insert into public.author_identities (author_id, platform, identity_value, normalized_value, verified, metadata)
select id, 'phone', '+1-604-555-0158', '16045550158', true, '{"source":"crm"}'::jsonb
from public.authors where email = 'daniel.park@bookleaf.ai'
on conflict do nothing;

insert into public.author_identities (author_id, platform, identity_value, normalized_value, verified, metadata)
select id, 'whatsapp', '+1-604-555-0158', '16045550158', true, '{"source":"whatsapp_sync"}'::jsonb
from public.authors where email = 'daniel.park@bookleaf.ai'
on conflict do nothing;

insert into public.author_identities (author_id, platform, identity_value, normalized_value, verified, metadata)
select id, 'instagram', '@anika.stories', 'anika.stories', true, '{"source":"onboarding"}'::jsonb
from public.authors where email = 'anika.sharma@bookleaf.ai'
on conflict do nothing;

insert into public.author_identities (author_id, platform, identity_value, normalized_value, verified, metadata)
select id, 'phone', '+91-98765-43210', '919876543210', true, '{"source":"crm"}'::jsonb
from public.authors where email = 'anika.sharma@bookleaf.ai'
on conflict do nothing;

insert into public.author_identities (author_id, platform, identity_value, normalized_value, verified, metadata)
select id, 'whatsapp', '+91-98765-43210', '919876543210', true, '{"source":"whatsapp_sync"}'::jsonb
from public.authors where email = 'anika.sharma@bookleaf.ai'
on conflict do nothing;
