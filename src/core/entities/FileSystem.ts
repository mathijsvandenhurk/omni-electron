/**
 * Core Entity: File System
 * Represents file system entities in the domain layer
 */

export interface FileSystemItem {
  name: string;
  path: string;
  type: 'file' | 'directory';
  size?: number;
  lastModified?: Date;
  extension?: string;
}

export interface DirectoryListing {
  path: string;
  items: FileSystemItem[];
  parent?: string;
}