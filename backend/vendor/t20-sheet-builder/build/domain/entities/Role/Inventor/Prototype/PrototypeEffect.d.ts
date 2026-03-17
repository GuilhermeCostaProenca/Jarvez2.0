import { PassiveEffect } from '../../../Ability';
import { type Equipment } from '../../../Inventory';
import { type EquipmentAlchemic } from '../../../Inventory/Equipment/EquipmentAlchemic/EquipmentAlchemic';
import { type EquipmentImprovement } from '../../../Inventory/Equipment/EquipmentImprovement/EquipmentImprovement';
import { type TransactionInterface } from '../../../Sheet/TransactionInterface';
export type PrototypeParams = {
    equipment: Equipment;
    improvement: EquipmentImprovement;
    choice: 'superiorItem';
} | {
    alchemicItems: EquipmentAlchemic[];
    choice: 'alchemicItems';
};
export declare class PrototypeEffect extends PassiveEffect {
    description: string;
    readonly payload: PrototypeParams;
    constructor(params: PrototypeParams);
    apply(transaction: TransactionInterface): void;
    private addSuperiorItem;
    private validateSuperiorItem;
    private validateAlchemicItems;
    private addAlchemicItems;
}
