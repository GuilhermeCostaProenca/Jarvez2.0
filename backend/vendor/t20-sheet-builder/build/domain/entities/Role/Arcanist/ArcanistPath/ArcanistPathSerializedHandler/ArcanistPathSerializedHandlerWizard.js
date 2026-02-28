"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistPathSerializedHandlerWizard = void 0;
const __1 = require("..");
const errors_1 = require("../../../../../errors");
const ArcanistPathSerializedHandler_1 = require("./ArcanistPathSerializedHandler");
class ArcanistPathSerializedHandlerWizard extends ArcanistPathSerializedHandler_1.ArcanistPathSerializedHandler {
    handle(request) {
        if (!request.focus) {
            throw new errors_1.SheetBuilderError('MISSING_WIZARD_FOCUS');
        }
        const focus = __1.ArcanistPathWizardFocusFactory.make(request.focus);
        return new __1.ArcanistPathWizard(focus);
    }
    shouldHandle(request) {
        return request.name === __1.ArcanistPathName.wizard;
    }
}
exports.ArcanistPathSerializedHandlerWizard = ArcanistPathSerializedHandlerWizard;
