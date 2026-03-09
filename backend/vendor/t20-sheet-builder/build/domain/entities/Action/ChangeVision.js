"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ChangeVision = void 0;
const Translatable_1 = require("../Translatable");
const Translator_1 = require("../Translator");
const Action_1 = require("./Action");
class ChangeVision extends Action_1.Action {
    constructor(params) {
        super(Object.assign(Object.assign({}, params), { type: 'changeVision' }));
    }
    execute() {
        const sheetVision = this.transaction.sheet.getSheetVision();
        sheetVision.changeVision(this.payload.vision);
    }
    getDescription() {
        const source = new Translatable_1.Translatable(this.payload.source).getTranslation();
        const vision = Translator_1.Translator.getVisionTranslation(this.payload.vision);
        return `${source}: ${vision} recebida.`;
    }
}
exports.ChangeVision = ChangeVision;
