"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.UnfulfilledRequirementError = void 0;
const SheetBuilderError_1 = require("./SheetBuilderError");
class UnfulfilledRequirementError extends SheetBuilderError_1.SheetBuilderError {
    constructor(requirement) {
        const message = `Requisito não preenchido: ${requirement.description}`;
        super(message);
        this.requirement = requirement;
        this.name = 'UnfulfilledRequirementError';
    }
}
exports.UnfulfilledRequirementError = UnfulfilledRequirementError;
