import { SelectableAttributesRace } from '../../SelectableAttributesRace';
import type { Attribute, Attributes } from '../../Sheet/Attributes';
import { RaceName } from '../RaceName';
import { type SerializedHuman } from '../SerializedRace';
import { Versatile } from './Versatile/Versatile';
import type { VersatileChoice } from './Versatile/VersatileChoice';
export declare class Human extends SelectableAttributesRace<SerializedHuman> {
    static readonly raceName = RaceName.human;
    static attributeModifiers: Partial<Attributes>;
    readonly abilities: {
        versatile: Versatile;
    };
    /**
 * Returns an instance of Human race.
 * @param selectedAttributes - 3 different attributes
 * @param versatileChoices - 2 skills or 1 skill and 1 general power
  **/
    constructor(selectedAttributes: Attribute[], versatileChoices?: VersatileChoice[]);
    addVersatilChoice(choice: VersatileChoice): void;
    serializeSpecific(): SerializedHuman;
    protected get restrictedAttributes(): string[];
    protected get fixedModifier(): number;
    protected get selectableQuantity(): number;
    get versatileChoices(): VersatileChoice[];
}
