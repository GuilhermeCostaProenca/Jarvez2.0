"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Handler = void 0;
const SheetBuilderError_1 = require("../../domain/errors/SheetBuilderError");
class Handler {
    setNext(handler) {
        this.nextHandler = handler;
        return handler;
    }
    execute(request) {
        if (this.shouldHandle(request)) {
            return this.handle(request);
        }
        if (this.nextHandler) {
            return this.nextHandler.execute(request);
        }
        throw new SheetBuilderError_1.SheetBuilderError('UNHANDLED_REQUEST');
    }
}
exports.Handler = Handler;
