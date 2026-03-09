"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.RegisterActivateableEffect = void 0;
const Translatable_1 = require("../Translatable");
const Action_1 = require("./Action");
class RegisterActivateableEffect extends Action_1.Action {
    constructor(params) {
        super(Object.assign(Object.assign({}, params), { type: 'registerActivateableEffect' }));
    }
    execute() {
        const effects = this.transaction.sheet.getSheetActivateableEffects();
        effects.register(this.payload.effect);
    }
    getDescription() {
        const source = new Translatable_1.Translatable(this.payload.effect.source).getTranslation();
        return `${source}: habilidade ativável adicionada.`;
    }
}
exports.RegisterActivateableEffect = RegisterActivateableEffect;
