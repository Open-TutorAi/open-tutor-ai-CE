export class ForbiddenError extends Error {
	constructor(message = 'Forbidden') {
		super(message);
		this.name = 'ForbiddenError';
	}
}

export class NotFoundError extends Error {
	constructor(message = 'Not Found') {
		super(message);
		this.name = 'NotFoundError';
	}
}
