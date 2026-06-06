-- Add image_subject to store the anime/movie/topic name Claude suggests for image search
ALTER TABLE posts ADD COLUMN IF NOT EXISTS image_subject TEXT;
