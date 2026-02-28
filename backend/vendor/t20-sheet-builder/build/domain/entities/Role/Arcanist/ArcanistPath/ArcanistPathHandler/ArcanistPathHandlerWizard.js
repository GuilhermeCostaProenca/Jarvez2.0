"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistPathHandlerWizard = void 0;
const errors_1 = require("../../../../../errors");
const ArcanisPathWizard_1 = require("../ArcanisPathWizard");
const ArcanistPath_1 = require("../ArcanistPath");
const ArcanistPathHandler_1 = require("./ArcanistPathHandler");
class ArcanistPathHandlerWizard extends ArcanistPathHandler_1.ArcanistPathHandler {
    handle(request) {
        if (!request.wizardFocus) {
            throw new errors_1.SheetBuilderError('MISSING_WIZARD_FOCUS');
        }
        const focus = ArcanisPathWizard_1.ArcanistPathWizardFocusFactory.make(request.wizardFocus);
        return new ArcanisPathWizard_1.ArcanistPathWizard(focus);
    }
    shouldHandle(request) {
        return request.path === ArcanistPath_1.ArcanistPathName.wizard;
    }
}
exports.ArcanistPathHandlerWizard = ArcanistPathHandlerWizard;
