"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ChooseOrigin = void 0;
const Translator_1 = require("../Translator");
const Action_1 = require("./Action");
class ChooseOrigin extends Action_1.Action {
    constructor(params) {
        super(Object.assign(Object.assign({}, params), { type: 'chooseOrigin' }));
    }
    execute() {
        const sheetOrigin = this.transaction.sheet.getSheetOrigin();
        sheetOrigin.chooseOrigin(this.payload.origin, this.transaction);
    }
    getDescription() {
        const origin = Translator_1.Translator.getOriginTranslation(this.payload.origin.name);
        return `Origem escolhida: ${origin}.`;
    }
}
exports.ChooseOrigin = ChooseOrigin;
