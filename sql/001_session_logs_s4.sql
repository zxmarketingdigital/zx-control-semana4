-- ZX Control Semana 4 — Session Logs
-- Aplique via: Supabase Dashboard > SQL Editor
-- Ou via MCP Supabase: apply_migration

CREATE TABLE IF NOT EXISTS session_logs_s4 (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  student_email TEXT,
  student_slug TEXT,
  platform TEXT,                      -- Darwin / Linux / Windows
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  duration_seconds INT,
  checkpoints JSONB,                  -- {step_1_base_s4: {status, detail, updated_at}, ...}
  errors JSONB,                       -- [{step, detail}, ...]
  optimizations JSONB,                -- [{step, suggestion}, ...]
  feedback TEXT,                      -- resposta free-text do aluno
  log_version TEXT DEFAULT '1.0',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- RLS
ALTER TABLE session_logs_s4 ENABLE ROW LEVEL SECURITY;

-- Apenas service_role pode inserir (edge function usa service key)
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'session_logs_s4' AND policyname = 'service_role_insert'
  ) THEN
    CREATE POLICY "service_role_insert"
      ON session_logs_s4
      FOR INSERT
      TO service_role
      WITH CHECK (true);
  END IF;
END $$;

-- Authenticated users podem ler todos os logs (para admin dashboard)
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'session_logs_s4' AND policyname = 'authenticated_read'
  ) THEN
    CREATE POLICY "authenticated_read"
      ON session_logs_s4
      FOR SELECT
      TO authenticated
      USING (true);
  END IF;
END $$;

-- Indices para queries frequentes
CREATE INDEX IF NOT EXISTS idx_session_logs_s4_created_at ON session_logs_s4(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_session_logs_s4_platform ON session_logs_s4(platform);
CREATE INDEX IF NOT EXISTS idx_session_logs_s4_student_email ON session_logs_s4(student_email);

-- Comentario
COMMENT ON TABLE session_logs_s4 IS 'Logs de sessao dos alunos da Semana 4 do ZX Control';
