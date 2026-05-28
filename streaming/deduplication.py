import apache_beam as beam
from apache_beam.coders import coders
from apache_beam.transforms.userstate import SetStateSpec


class DeduplicatePedidos(beam.DoFn):
    """Deduplica eventos por pedido_id usando estado Beam.

    La entrada debe ser KV(pedido_id, evento_dict).
    Emite el evento si el pedido_id no se ha visto antes.
    """

    SEEN_IDS = SetStateSpec(
        "seen_ids",
        coders.VarIntCoder()
    )

    def process(self, element, seen_ids=beam.DoFn.StateParam(SEEN_IDS)):
        pedido_id, event = element
        if pedido_id is not None and pedido_id not in seen_ids:
            seen_ids.add(pedido_id)
            yield event
