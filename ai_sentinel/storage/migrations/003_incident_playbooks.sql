-- Migration to add playbook support to real incidents
ALTER TABLE incidents ADD COLUMN playbook TEXT;
