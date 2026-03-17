"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Action = void 0;
class Action {
    constructor(params) {
        this.type = params.type;
        this.payload = params.payload;
        this.transaction = params.transaction;
        this.description = this.getDescription();
    }
}
exports.Action = Action;
