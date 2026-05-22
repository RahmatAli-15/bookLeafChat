-- Mock seed data for BookLeaf

do $$
declare
    a1 uuid;
    a2 uuid;
    a3 uuid;
    b1 uuid;
    b2 uuid;
    b3 uuid;
    q1 uuid;
    q2 uuid;
begin
    insert into public.authors (full_name, email, genre, country)
    values
        ('Maya Richardson', 'maya.richardson@bookleaf.ai', 'Self-Help', 'United States'),
        ('Daniel Park', 'daniel.park@bookleaf.ai', 'Business', 'Canada'),
        ('Anika Sharma', 'anika.sharma@bookleaf.ai', 'Fantasy', 'India')
    on conflict (email) do update set full_name = excluded.full_name
    returning id into a1;

    select id into a1 from public.authors where email = 'maya.richardson@bookleaf.ai';
    select id into a2 from public.authors where email = 'daniel.park@bookleaf.ai';
    select id into a3 from public.authors where email = 'anika.sharma@bookleaf.ai';

    insert into public.books (author_id, title, isbn, publication_date, status, support_tier)
    values
        (a1, 'Reset Your Morning', '9780000000001', '2024-05-01', 'published', 'premium'),
        (a2, 'The Lean Creator', '9780000000002', '2023-09-17', 'published', 'standard'),
        (a3, 'Stars of Velora', '9780000000003', '2025-01-11', 'published', 'premium')
    on conflict (isbn) do nothing;

    select id into b1 from public.books where isbn = '9780000000001';
    select id into b2 from public.books where isbn = '9780000000002';
    select id into b3 from public.books where isbn = '9780000000003';

    insert into public.add_on_services (book_id, service_name, service_type, monthly_fee, status)
    values
        (b1, 'Priority Reader Support', 'support', 49.00, 'active'),
        (b1, 'SEO Metadata Pack', 'marketing', 29.00, 'active'),
        (b2, 'Audiobook Snippet Assistant', 'content', 19.00, 'active'),
        (b3, 'Launch Campaign Automation', 'marketing', 79.00, 'active')
    on conflict do nothing;

    insert into public.queries (channel, customer_name, customer_email, message, intent, status, response_time_ms, book_id, metadata)
    values
        ('web-chat', 'Emma Collins', 'emma.collins@example.com', 'My download link for Stars of Velora expired. Can you resend it?', 'download_issue', 'resolved', 1840, b3, '{"source":"website","sentiment":"neutral"}'),
        ('email', 'Noah Wright', 'noah.wright@example.com', 'Need invoice for Priority Reader Support add-on.', 'billing', 'open', null, b1, '{"source":"inbox","sentiment":"positive"}')
    returning id into q1;

    select id into q1 from public.queries where customer_email = 'emma.collins@example.com' order by created_at desc limit 1;
    select id into q2 from public.queries where customer_email = 'noah.wright@example.com' order by created_at desc limit 1;

    insert into public.escalations (query_id, escalation_level, reason, assigned_to, priority, status)
    values
        (q2, 2, 'Invoice requires manual verification before issue.', 'billing.team@bookleaf.ai', 'high', 'open')
    on conflict do nothing;
end $$;
