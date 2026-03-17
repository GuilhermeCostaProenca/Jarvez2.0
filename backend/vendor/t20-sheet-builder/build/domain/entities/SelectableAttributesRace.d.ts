import { type SerializedRaces } from './Race';
import { Race } from './Race/Race';
import type { RaceName } from './Race/RaceName';
import type { Attribute, Attributes } from './Sheet/Attributes';
export declare abstract class SelectableAttributesRace<S extends SerializedRaces = SerializedRaces> extends Race<S> {
    readonly selectedAttributes: Attribute[];
    readonly attributeModifiers: Partial<Attributes>;
    constructor(selectedAttributes: Attribute[], name: RaceName, initialAttributeModifiers?: Partial<Attributes>);
    private validateSelectedAttributes;
    protected abstract get restrictedAttributes(): string[];
    protected abstract get selectableQuantity(): number;
    protected abstract get fixedModifier(): number;
}
