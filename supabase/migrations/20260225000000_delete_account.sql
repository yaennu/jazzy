-- ============================================================
-- RPC function for authenticated account deletion
-- ============================================================

CREATE OR REPLACE FUNCTION public.delete_account()
RETURNS TEXT AS $$
DECLARE
  v_uid UUID;
BEGIN
  v_uid := auth.uid();

  IF v_uid IS NULL THEN
    RETURN 'not_authenticated';
  END IF;

  -- Delete from public.users (cascades to recommendations)
  DELETE FROM public.users WHERE user_id = v_uid;

  -- Delete from auth.users
  DELETE FROM auth.users WHERE id = v_uid;

  RETURN 'success';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
