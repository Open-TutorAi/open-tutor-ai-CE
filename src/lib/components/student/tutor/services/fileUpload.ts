/**
 * File Upload Helper Module
 * 
 * Handles file uploads from various sources including
 * local files, Google Drive, web URLs, and YouTube videos.
 * 
 * Extracted from Chat.svelte for better separation of concerns.
 */

import { v4 as uuidv4 } from 'uuid';
import { toast } from 'svelte-sonner';

import { processWeb, processYoutubeVideo } from '$lib/apis/retrieval';
import { uploadFile } from '$lib/apis/files';
import { TUTOR_API_BASE_URL } from '$lib/constants';

import type { ChatFile, FileUploadItem } from './types';

/**
 * Creates a file item object for tracking upload status
 */
export function createFileItem(
	type: 'file' | 'doc' | 'image',
	name: string,
	url?: string
): FileUploadItem {
	return {
		type,
		file: '',
		id: null,
		url: url || '',
		name,
		collection_name: '',
		status: 'uploading',
		error: '',
		itemId: uuidv4(),
		size: 0
	};
}

/**
 * Uploads a file from Google Drive
 */
export async function uploadGoogleDriveFile(
	fileData: {
		id: string;
		name: string;
		url: string;
		headers: { Authorization: string };
	},
	i18n: any
): Promise<FileUploadItem | null> {
	console.log('Starting uploadGoogleDriveFile with:', {
		id: fileData.id,
		name: fileData.name,
		url: fileData.url
	});

	// Validate input
	if (!fileData?.id || !fileData?.name || !fileData?.url || !fileData?.headers?.Authorization) {
		throw new Error('Invalid file data provided');
	}

	const fileItem = createFileItem('file', fileData.name, fileData.url);

	try {
		console.log('Processing web file with URL:', fileData.url);

		// Configure fetch options
		const fetchOptions: RequestInit = {
			headers: {
				Authorization: fileData.headers.Authorization,
				Accept: '*/*'
			},
			method: 'GET'
		};

		// Fetch the file
		console.log('Fetching file content from Google Drive...');
		const fileResponse = await fetch(fileData.url, fetchOptions);

		if (!fileResponse.ok) {
			const errorText = await fileResponse.text();
			throw new Error(`Failed to fetch file (${fileResponse.status}): ${errorText}`);
		}

		// Get content type
		const contentType = fileResponse.headers.get('content-type') || 'application/octet-stream';
		console.log('Response received with content-type:', contentType);

		// Convert to blob
		console.log('Converting response to blob...');
		const fileBlob = await fileResponse.blob();

		if (fileBlob.size === 0) {
			throw new Error('Retrieved file is empty');
		}

		console.log('Blob created:', {
			size: fileBlob.size,
			type: fileBlob.type || contentType
		});

		// Create File object
		const file = new File([fileBlob], fileData.name, {
			type: fileBlob.type || contentType
		});

		console.log('File object created:', {
			name: file.name,
			size: file.size,
			type: file.type
		});

		if (file.size === 0) {
			throw new Error('Created file is empty');
		}

		// Upload to server
		console.log('Uploading file to server...');
		const uploadedFile = await uploadFile(localStorage.token, file);

		if (!uploadedFile) {
			throw new Error('Server returned null response for file upload');
		}

		console.log('File uploaded successfully:', uploadedFile);

		// Update file item
		fileItem.status = 'uploaded';
		fileItem.file = uploadedFile;
		fileItem.id = uploadedFile.id;
		fileItem.size = file.size;
		fileItem.collection_name = uploadedFile?.meta?.collection_name;
		fileItem.url = `${TUTOR_API_BASE_URL}/files/${uploadedFile.id}`;

		toast.success(i18n.t('File uploaded successfully'));
		return fileItem;
	} catch (e: any) {
		console.error('Error uploading file:', e);
		toast.error(
			i18n.t('Error uploading file: {{error}}', {
				error: e.message || 'Unknown error'
			})
		);
		return null;
	}
}

/**
 * Uploads content from a web URL
 */
export async function uploadWebContent(
	url: string,
	i18n: any
): Promise<FileUploadItem | null> {
	console.log('Uploading web content from:', url);

	const fileItem: FileUploadItem = {
		type: 'doc',
		name: url,
		collection_name: '',
		status: 'uploading',
		url,
		error: '',
		itemId: uuidv4()
	};

	try {
		const res = await processWeb(localStorage.token, '', url);

		if (res) {
			fileItem.status = 'uploaded';
			fileItem.collection_name = res.collection_name;
			fileItem.file = {
				...res.file,
				...fileItem.file
			};

			return fileItem;
		}

		return null;
	} catch (e: any) {
		console.error('Error uploading web content:', e);
		toast.error(JSON.stringify(e));
		return null;
	}
}

/**
 * Uploads YouTube video transcription
 */
export async function uploadYoutubeTranscription(
	url: string,
	i18n: any
): Promise<FileUploadItem | null> {
	console.log('Uploading YouTube transcription from:', url);

	const fileItem: FileUploadItem = {
		type: 'doc',
		name: url,
		collection_name: '',
		status: 'uploading',
		context: 'full',
		url,
		error: '',
		itemId: uuidv4()
	};

	try {
		const res = await processYoutubeVideo(localStorage.token, url);

		if (res) {
			fileItem.status = 'uploaded';
			fileItem.collection_name = res.collection_name;
			fileItem.file = {
				...res.file,
				...fileItem.file
			};

			return fileItem;
		}

		return null;
	} catch (e: any) {
		console.error('Error uploading YouTube transcription:', e);
		toast.error(`${e}`);
		return null;
	}
}

/**
 * Validates file before upload
 */
export function validateFile(
	file: File,
	maxSize?: number,
	allowedTypes?: string[]
): { valid: boolean; error?: string } {
	if (maxSize && file.size > maxSize) {
		return {
			valid: false,
			error: `File size exceeds maximum allowed size of ${formatFileSize(maxSize)}`
		};
	}

	if (allowedTypes && allowedTypes.length > 0) {
		const fileType = file.type.toLowerCase();
		const isAllowed = allowedTypes.some(
			(type) => fileType === type.toLowerCase() || fileType.startsWith(type.toLowerCase())
		);

		if (!isAllowed) {
			return {
				valid: false,
				error: `File type ${file.type} is not allowed. Allowed types: ${allowedTypes.join(', ')}`
			};
		}
	}

	return { valid: true };
}

/**
 * Formats file size for display
 */
export function formatFileSize(bytes: number): string {
	if (bytes === 0) return '0 Bytes';

	const k = 1024;
	const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
	const i = Math.floor(Math.log(bytes) / Math.log(k));

	return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Gets the file extension from a filename
 */
export function getFileExtension(filename: string): string {
	const lastDot = filename.lastIndexOf('.');
	return lastDot !== -1 ? filename.substring(lastDot + 1).toLowerCase() : '';
}

/**
 * Determines file type from extension or mime type
 */
export function getFileType(
	filename: string,
	mimeType?: string
): 'image' | 'document' | 'video' | 'audio' | 'other' {
	const extension = getFileExtension(filename);
	const type = mimeType?.toLowerCase() || '';

	// Image types
	const imageExtensions = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp', 'ico'];
	if (imageExtensions.includes(extension) || type.startsWith('image/')) {
		return 'image';
	}

	// Video types
	const videoExtensions = ['mp4', 'webm', 'ogg', 'avi', 'mov', 'wmv', 'flv'];
	if (videoExtensions.includes(extension) || type.startsWith('video/')) {
		return 'video';
	}

	// Audio types
	const audioExtensions = ['mp3', 'wav', 'ogg', 'aac', 'flac', 'wma'];
	if (audioExtensions.includes(extension) || type.startsWith('audio/')) {
		return 'audio';
	}

	// Document types
	const docExtensions = [
		'pdf',
		'doc',
		'docx',
		'txt',
		'rtf',
		'odt',
		'xls',
		'xlsx',
		'ppt',
		'pptx',
		'md',
		'csv'
	];
	if (
		docExtensions.includes(extension) ||
		type.includes('document') ||
		type.includes('text') ||
		type.includes('pdf')
	) {
		return 'document';
	}

	return 'other';
}

/**
 * Removes duplicate files from an array
 */
export function deduplicateFiles(files: ChatFile[]): ChatFile[] {
	return files.filter(
		(item, index, array) =>
			array.findIndex((i) => JSON.stringify(i) === JSON.stringify(item)) === index
	);
}

/**
 * Filters files by type
 */
export function filterFilesByType(files: ChatFile[], types: string[]): ChatFile[] {
	return files.filter((file) => types.includes(file.type));
}

/**
 * Checks if any files are still uploading
 */
export function hasUploadingFiles(files: FileUploadItem[]): boolean {
	return files.some(
		(file) => file.type !== 'image' && file.status === 'uploading'
	);
}

/**
 * Gets files that are ready for chat
 */
export function getReadyFiles(files: FileUploadItem[]): FileUploadItem[] {
	return files.filter((file) => file.status === 'uploaded');
}

/**
 * Merges chat files with user files, removing duplicates
 */
export function mergeFiles(chatFiles: ChatFile[], userFiles: FileUploadItem[]): ChatFile[] {
	const docTypes = ['doc', 'file', 'collection'];
	const newFiles = userFiles.filter((item) => docTypes.includes(item.type));

	return deduplicateFiles([...chatFiles, ...newFiles] as ChatFile[]);
}
