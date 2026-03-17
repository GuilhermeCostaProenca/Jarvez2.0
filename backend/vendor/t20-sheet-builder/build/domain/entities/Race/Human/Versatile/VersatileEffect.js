"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.VersatileEffect = void 0;
const PassiveEffect_1 = require("../../../Ability/PassiveEffect");
const SheetBuilderError_1 = require("../../../../errors/SheetBuilderError");
const RaceAbilityName_1 = require("../../RaceAbilityName");
class VersatileEffect extends PassiveEffect_1.PassiveEffect {
    get description() {
        return 'Você se torna treinado em duas perícias a sua escolha (não precisam ser da sua classe). Você pode trocar uma dessas perícias por um poder geral a sua escolha.';
    }
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.versatile);
        this.choices = [];
    }
    addChoice(newChoice) {
        if (this.choices.length >= 2) {
            throw new SheetBuilderError_1.SheetBuilderError('EXCEEDED_CHOICES_QUANTITY');
        }
        const found = this.choices.find(choice => choice.name === newChoice.name);
        if (found) {
            throw new SheetBuilderError_1.SheetBuilderError('REPEATED_VERSATILE_CHOICE');
        }
        const isPreviousChoicePower = this.choices.some(choice => choice.type === 'power');
        if (newChoice.type === 'power' && isPreviousChoicePower) {
            throw new SheetBuilderError_1.SheetBuilderError('FORBIDDEN_TWO_POWERS');
        }
        this.choices.push(newChoice);
    }
    apply(transaction) {
        if (this.choices.length !== 2) {
            throw new SheetBuilderError_1.SheetBuilderError('MISSING_CHOICES');
        }
        this.choices.forEach(choice => {
            choice.addToSheet(transaction, this.source);
        });
    }
}
exports.VersatileEffect = VersatileEffect;
