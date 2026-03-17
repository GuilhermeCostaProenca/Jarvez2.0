"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PreviewContextError = void 0;
class PreviewContextError extends Error {
    constructor() {
        super(...arguments);
        this.name = 'PreviewContextError';
    }
}
exports.PreviewContextError = PreviewContextError;
