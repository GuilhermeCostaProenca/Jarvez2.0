import { type ContextInterface } from '../Context';
import { type PerLevelModifiersList, type FixedModifiersListInterface } from '../Modifier';
import { type ModifierInterface } from '../Modifier/ModifierInterface';
import { type PerLevelModifierInterface } from '../Modifier/PerLevelModifier/PerLevelModifierInterface';
import { type Points } from '../Points/Points';
import { type Attributes } from './Attributes';
import { type Level } from './Level';
import { type SerializedSheetPoints } from './SerializedSheet/SerializedSheetInterface';
import { type SheetInterface } from './SheetInterface';
import { type SheetPointsInterface } from './SheetPointsInterface';
export declare class SheetPoints implements SheetPointsInterface {
    private readonly points;
    constructor(points: Points);
    serialize(sheet: SheetInterface, context: ContextInterface): SerializedSheetPoints;
    getFixedModifiers(): FixedModifiersListInterface;
    getPerLevelModifiers(): PerLevelModifiersList;
    getModifiers(): ModifierInterface[];
    addFixedModifier(modifier: ModifierInterface): void;
    addPerLevelModifier(modifier: PerLevelModifierInterface): void;
    getMax(attributes: Attributes, level: Level): number;
}
