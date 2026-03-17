"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SheetBuilderError = void 0;
class SheetBuilderError extends Error {
    constructor() {
        super(...arguments);
        this.name = 'SheetBuilderError';
    }
}
exports.SheetBuilderError = SheetBuilderError;
