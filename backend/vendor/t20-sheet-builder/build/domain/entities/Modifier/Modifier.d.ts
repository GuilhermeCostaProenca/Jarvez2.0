import type { Attribute, Attributes } from '../Sheet/Attributes';
import type { TranslatableName } from '../Translator';
import type { ModifierInterface, ModifierType, ModifierAppliableValueCalculatorInterface, SerializedModifier } from './ModifierInterface';
export type ModifierParams = {
    source: TranslatableName;
    value: number;
    type: ModifierType;
    attributeBonuses?: Set<Attribute>;
};
export declare abstract class Modifier implements ModifierInterface {
    readonly attributeBonuses: Attribute[];
    readonly source: TranslatableName;
    readonly baseValue: number;
    readonly type: ModifierType;
    constructor(params: ModifierParams);
    getAppliableValue(calculator: ModifierAppliableValueCalculatorInterface): number;
    getTotalAttributeBonuses(attributes: Attributes): number;
    serialize(appliableValueCalculator: ModifierAppliableValueCalculatorInterface, attributes: Attributes): SerializedModifier;
}
