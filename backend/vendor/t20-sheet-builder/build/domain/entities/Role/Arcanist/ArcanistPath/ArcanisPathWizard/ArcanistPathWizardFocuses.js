"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistPathWizardFocuses = void 0;
const ArcanistPathWizardFocusStaff_1 = require("./ArcanistPathWizardFocusStaff");
const ArcanistPathWizardFocusWand_1 = require("./ArcanistPathWizardFocusWand");
class ArcanistPathWizardFocuses {
    static getAll() {
        return [
            ArcanistPathWizardFocusWand_1.ArcanistPathWizardFocusWand,
            ArcanistPathWizardFocusStaff_1.ArcanistPathWizardFocusStaff,
        ];
    }
}
exports.ArcanistPathWizardFocuses = ArcanistPathWizardFocuses;
