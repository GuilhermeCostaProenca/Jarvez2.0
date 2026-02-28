"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Transaction = void 0;
const ActionsQueue_1 = require("../ActionsQueue");
const BuildStep_1 = require("../BuildStep");
class Transaction {
    constructor(sheet) {
        this.sheet = sheet;
        this.actionsQueue = new ActionsQueue_1.ActionsQueue();
    }
    run(action) {
        this.actionsQueue.enqueue(action);
        action.execute();
    }
    commit() {
        const buildSteps = [];
        while (this.actionsQueue.getSize() > 0) {
            const action = this.actionsQueue.dequeue();
            buildSteps.push(new BuildStep_1.BuildStep(action));
        }
        this.sheet.pushBuildSteps(...buildSteps);
    }
}
exports.Transaction = Transaction;
