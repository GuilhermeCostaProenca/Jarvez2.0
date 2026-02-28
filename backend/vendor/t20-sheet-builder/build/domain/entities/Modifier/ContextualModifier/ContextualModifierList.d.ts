import { type SerializedSheetContextualModifiersList } from '../..';
import { type Context } from '../../Context';
import type { Attributes } from '../../Sheet/Attributes';
import { type SheetInterface } from '../../Sheet/SheetInterface';
import { ModifiersList } from '../ModifiersList';
import type { ContextualModifierInterface } from './ContextualModifierInterface';
import type { ContextualModifiersListInterface } from './ContextualModifiersListInterface';
export declare class ContextualModifiersList extends ModifiersList<ContextualModifierInterface> implements ContextualModifiersListInterface {
    serialize(sheet: SheetInterface, context: Context): SerializedSheetContextualModifiersList;
    getMaxTotal(attributes: Attributes): number;
}
