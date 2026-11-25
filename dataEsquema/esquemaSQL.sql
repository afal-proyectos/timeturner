-- ========================================================
-- ESQUEMA DE BASE DE DATOS PARA LEERJUNTOS (SUPABASE / POSTGRESQL)
-- ========================================================

-- 1. Habilitar extensión para generación de UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. TABLA DE PERFILES DE USUARIO (Vinculada a Supabase Auth)
CREATE TABLE IF NOT EXISTS public.profiles (
    id_usuario UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    apodo VARCHAR(100) NOT NULL,
    rol VARCHAR(50) DEFAULT 'Lector',
    fecha_registro TIMESTAMPTZ DEFAULT NOW()
);

-- 3. TABLA DE LIBROS
CREATE TABLE IF NOT EXISTS public.books (
    id_libro UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID NOT NULL REFERENCES public.profiles(id_usuario) ON DELETE CASCADE,
    titulo VARCHAR(255) NOT NULL,
    autor VARCHAR(255) NOT NULL,
    genero VARCHAR(100),
    total_paginas INT NOT NULL CHECK (total_paginas > 0),
    portada_url TEXT,
    fecha_creacion TIMESTAMPTZ DEFAULT NOW()
);

-- 4. TABLA DE SESIONES DE LECTURA
CREATE TABLE IF NOT EXISTS public.reading_sessions (
    id_sesion UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    libro_id UUID NOT NULL REFERENCES public.books(id_libro) ON DELETE CASCADE,
    usuario_id UUID NOT NULL REFERENCES public.profiles(id_usuario) ON DELETE CASCADE,
    pagina_inicio INT NOT NULL CHECK (pagina_inicio >= 0),
    pagina_fin INT CHECK (pagina_fin >= pagina_inicio),
    inicio_utc TIMESTAMPTZ NOT NULL,
    fin_utc TIMESTAMPTZ,
    minutos_pausa DOUBLE PRECISION DEFAULT 0.0,
    estado VARCHAR(50) NOT NULL DEFAULT 'INACTIVA',
    fecha_registro TIMESTAMPTZ DEFAULT NOW()
);

-- ========================================================
-- POLÍTICAS DE SEGURIDAD A NIVEL DE FILA (ROW LEVEL SECURITY - RLS)
-- ========================================================

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.books ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reading_sessions ENABLE ROW LEVEL SECURITY;

-- Políticas para Profiles
CREATE POLICY "Los usuarios pueden leer su propio perfil" 
    ON public.profiles FOR SELECT USING (auth.uid() = id_usuario);

CREATE POLICY "Los usuarios pueden actualizar su propio perfil" 
    ON public.profiles FOR UPDATE USING (auth.uid() = id_usuario);

-- Políticas para Books
CREATE POLICY "Los usuarios pueden ver únicamente sus libros" 
    ON public.books FOR SELECT USING (auth.uid() = usuario_id);

CREATE POLICY "Los usuarios pueden insertar sus propios libros" 
    ON public.books FOR INSERT WITH CHECK (auth.uid() = usuario_id);

CREATE POLICY "Los usuarios pueden actualizar sus propios libros" 
    ON public.books FOR UPDATE USING (auth.uid() = usuario_id);

CREATE POLICY "Los usuarios pueden eliminar sus propios libros" 
    ON public.books FOR DELETE USING (auth.uid() = usuario_id);

-- Políticas para Reading Sessions
CREATE POLICY "Los usuarios pueden ver sus propias sesiones de lectura" 
    ON public.reading_sessions FOR SELECT USING (auth.uid() = usuario_id);

CREATE POLICY "Los usuarios pueden insertar sus propias sesiones" 
    ON public.reading_sessions FOR INSERT WITH CHECK (auth.uid() = usuario_id);

CREATE POLICY "Los usuarios pueden actualizar sus propias sesiones" 
    ON public.reading_sessions FOR UPDATE USING (auth.uid() = usuario_id);


-- Permitir acceso temporal de lectura y escritura a la tabla profiles durante desarrollo
CREATE POLICY "Permite acceso anonimo temporal a profiles" 
    ON public.profiles FOR ALL USING (true) WITH CHECK (true);