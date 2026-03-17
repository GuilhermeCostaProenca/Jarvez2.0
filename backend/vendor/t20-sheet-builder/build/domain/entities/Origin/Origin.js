"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Origin = void 0;
const AddEquipment_1 = require("../Action/AddEquipment");
const SheetBuilderError_1 = require("../../errors/SheetBuilderError");
class Origin {
    constructor(chosenBenefits, benefits) {
        this.chosenBenefits = chosenBenefits;
        this.benefits = benefits;
        this.validateChosenBenefits();
    }
    addToSheet(transaction) {
        this.addEquipments(transaction);
        this.applyBenefits(transaction);
    }
    serializeBenefits() {
        return this.chosenBenefits.map(benefit => benefit.serialize());
    }
    serializeEquipments() {
        return this.equipments.map(equipment => equipment.serialize());
    }
    applyBenefits(transaction) {
        this.chosenBenefits.forEach(benefit => {
            benefit.apply(transaction, this.name);
        });
    }
    addEquipments(transaction) {
        this.equipments.forEach(equipment => {
            transaction.run(new AddEquipment_1.AddEquipment({
                payload: {
                    equipment,
                    source: this.name,
                },
                transaction,
            }));
        });
    }
    validateChosenBenefits() {
        if (this.chosenBenefits.length !== 2) {
            throw new SheetBuilderError_1.SheetBuilderError('INVALID_ORIGIN_BENEFITS');
        }
        this.chosenBenefits.forEach(benefit => {
            benefit.validate(this.benefits);
        });
    }
}
exports.Origin = Origin;
