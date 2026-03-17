"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ActionsQueue = void 0;
const SheetBuilderError_1 = require("../errors/SheetBuilderError");
class ActionsQueue {
    constructor() {
        this.items = [];
    }
    enqueue(item) {
        this.items.push(item);
    }
    dequeue() {
        const item = this.items.shift();
        if (!item) {
            throw new SheetBuilderError_1.SheetBuilderError('EMPTY_QUEUE');
        }
        return item;
    }
    getSize() {
        return this.items.length;
    }
}
exports.ActionsQueue = ActionsQueue;
