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

-- 1. TABLA DE GRUPOS
CREATE TABLE IF NOT EXISTS public.groups (
    id_grupo UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(150) NOT NULL,
    codigo_acceso VARCHAR(6) UNIQUE NOT NULL,
    admin_id UUID NOT NULL REFERENCES public.profiles(id_usuario) ON DELETE CASCADE,
    fecha_creacion TIMESTAMPTZ DEFAULT NOW()
);

-- 2. TABLA DE MIEMBROS DE GRUPO
CREATE TABLE IF NOT EXISTS public.group_members (
    id_grupo UUID NOT NULL REFERENCES public.groups(id_grupo) ON DELETE CASCADE,
    id_usuario UUID NOT NULL REFERENCES public.profiles(id_usuario) ON DELETE CASCADE,
    fecha_union TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id_grupo, id_usuario)
);

-- 3. TABLA DE MENSAJES Y STICKERS DEL CHAT
CREATE TABLE IF NOT EXISTS public.messages (
    id_mensaje UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    grupo_id UUID NOT NULL REFERENCES public.groups(id_grupo) ON DELETE CASCADE,
    usuario_id UUID NOT NULL REFERENCES public.profiles(id_usuario) ON DELETE CASCADE,
    informacion TEXT NOT NULL,
    tipo VARCHAR(20) DEFAULT 'TEXTO', -- 'TEXTO', 'STICKER', 'ANIMO'
    fecha_envio TIMESTAMPTZ DEFAULT NOW()
);

-- ========================================================
-- POLÍTICAS DE SEGURIDAD (RLS) - LECTURA Y ESCRITURA CRUZADA
-- ========================================================

ALTER TABLE public.groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.group_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

-- Políticas para Acceso Temporal / Desarrollo (Sprint 4)
CREATE POLICY "Permite acceso a grupos" ON public.groups FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Permite acceso a miembros" ON public.group_members FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Permite acceso a mensajes" ON public.messages FOR ALL USING (true) WITH CHECK (true);

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