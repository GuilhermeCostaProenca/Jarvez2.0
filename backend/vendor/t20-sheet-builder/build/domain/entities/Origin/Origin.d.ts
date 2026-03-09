import type { Equipment } from '../Inventory/Equipment/Equipment';
import { type TransactionInterface } from '../Sheet/TransactionInterface';
import type { OriginBenefit } from './OriginBenefit/OriginBenefit';
import { type OriginBenefits } from './OriginBenefit/OriginBenefits';
import { type SerializedOriginBenefit, type SerializedOriginBenefits } from './OriginBenefit/SerializedOriginBenefit';
import type { OriginName } from './OriginName';
import { type SerializedSheetOrigin, type SerializedOrigins } from './SerializedOrigin';
export type OriginInterface<Sb extends SerializedOriginBenefit = SerializedOriginBenefits, So extends SerializedOrigins = SerializedOrigins> = {
    name: OriginName;
    equipments: Equipment[];
    chosenBenefits: Array<OriginBenefit<Sb>>;
    benefits: OriginBenefits;
    addToSheet(transaction: TransactionInterface): void;
    serialize(): So;
};
export declare abstract class Origin<Sb extends SerializedOriginBenefit = SerializedOriginBenefit, So extends SerializedOrigins = SerializedOrigins> implements OriginInterface<Sb, So> {
    readonly chosenBenefits: Array<OriginBenefit<Sb>>;
    readonly benefits: OriginBenefits;
    abstract name: OriginName;
    abstract equipments: Equipment[];
    constructor(chosenBenefits: Array<OriginBenefit<Sb>>, benefits: OriginBenefits);
    addToSheet(transaction: TransactionInterface): void;
    abstract serialize(): SerializedSheetOrigin<So>;
    protected serializeBenefits(): Sb[];
    protected serializeEquipments(): import("..").SerializedSheetEquipment<import("..").EquipmentName>[];
    private applyBenefits;
    private addEquipments;
    private validateChosenBenefits;
}
