import { type ContextInterface } from '../Context';
import { type DefenseInterface } from '../Defense/DefenseInterface';
import { type FixedModifierInterface } from '../Modifier/FixedModifier/FixedModifier';
import { type Attributes } from './Attributes';
import { type SerializedSheetDefense } from './SerializedSheet/SerializedSheetInterface';
import { type SheetDefenseInterface } from './SheetDefenseInterface';
import { type SheetInterface } from './SheetInterface';
export declare class SheetDefense implements SheetDefenseInterface {
    private readonly defense;
    constructor(defense?: DefenseInterface);
    addFixedModifier(modifier: FixedModifierInterface): void;
    getTotal(attributes: Attributes, armorBonus: number, shieldBonus: number): number;
    getDefense(): DefenseInterface;
    serialize(sheet: SheetInterface, context?: ContextInterface): SerializedSheetDefense;
}
