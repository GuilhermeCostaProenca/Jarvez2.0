import type { FixedModifiersListInterface } from '../Modifier/FixedModifier/FixedModifiersList';
import { type ModifierInterface } from '../Modifier/ModifierInterface';
import type { Attributes } from '../Sheet/Attributes';
import type { DefenseInterface } from './DefenseInterface';
export declare class DefenseFake implements DefenseInterface {
    attribute: keyof Attributes;
    total: number;
    fixedModifiers: FixedModifiersListInterface;
    getTotal(): number;
    addFixedModifier(modifier: ModifierInterface): void;
}
