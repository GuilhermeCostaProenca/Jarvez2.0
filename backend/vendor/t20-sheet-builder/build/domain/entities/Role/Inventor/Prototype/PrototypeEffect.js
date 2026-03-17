"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PrototypeEffect = void 0;
const Ability_1 = require("../../../Ability");
const AddEquipment_1 = require("../../../Action/AddEquipment");
const RoleAbilityName_1 = require("../../RoleAbilityName");
class PrototypeEffect extends Ability_1.PassiveEffect {
    constructor(params) {
        super(RoleAbilityName_1.RoleAbilityName.prototype);
        this.description = 'Você começa o jogo com um item'
            + ' superior, ou com 10 itens alquímicos, com preço total'
            + ' de até T$ 500. Veja o Capítulo 3: Equipamento'
            + ' para a lista de itens.';
        this.payload = params;
        if (params.choice === 'superiorItem') {
            params.equipment.addImprovement(params.improvement);
            this.validateSuperiorItem(params.equipment);
        }
        if (params.choice === 'alchemicItems') {
            this.validateAlchemicItems(params.alchemicItems);
        }
    }
    apply(transaction) {
        if (this.payload.choice === 'superiorItem') {
            this.addSuperiorItem(transaction, this.payload.equipment);
        }
        else {
            this.addAlchemicItems(transaction, this.payload.alchemicItems);
        }
    }
    addSuperiorItem(transaction, equipment) {
        transaction.run(new AddEquipment_1.AddEquipment({
            payload: {
                equipment,
                source: this.source,
            },
            transaction,
        }));
    }
    validateSuperiorItem(equipment) {
        if (equipment.getTotalPrice() > 2000) {
            throw new Error('SUPERIOR_ITEM_PRICE_LIMIT_REACHED');
        }
    }
    validateAlchemicItems(alchemicItems) {
        const totalPrice = alchemicItems.reduce((total, item) => total + item.price, 0);
        if (totalPrice > 500) {
            throw new Error('ALCHEMIC_PRICE_LIMIT_REACHED');
        }
    }
    addAlchemicItems(transaction, alchemicItems) {
        alchemicItems.forEach(item => {
            transaction.run(new AddEquipment_1.AddEquipment({
                payload: {
                    equipment: item,
                    source: this.source,
                },
                transaction,
            }));
        });
    }
}
exports.PrototypeEffect = PrototypeEffect;
