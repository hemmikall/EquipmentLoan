import {
  checkPluginVersion,
  type InvenTreePluginContext
} from '@inventreedb/ui';
import {
  ActionIcon,
  Alert,
  Badge,
  Button,
  Card,
  Center,
  Group,
  Loader,
  Modal,
  Pagination,
  Select,
  SimpleGrid,
  Stack,
  Table,
  Tabs,
  Text,
  Textarea,
  TextInput,
  Title,
  Tooltip
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconCheck, IconChevronDown, IconRefresh } from '@tabler/icons-react';
import { useCallback, useEffect, useState } from 'react';

interface Loan {
  id: number;
  borrower_username: string;
  part_name: string;
  part_id: number;
  quantity: number;
  date_borrowed: string;
  date_due: string | null;
  date_returned: string | null;
  status: string;
  status_display: string;
  is_overdue: boolean;
  days_borrowed: number;
}

interface LoanDetail extends Loan {
  notes: string;
  return_notes: string;
  created_by_username: string;
  date_created: string;
  date_updated: string;
  days_overdue: number;
  history: any[];
}

interface Statistics {
  total_loans: number;
  active_loans: number;
  returned_loans: number;
  lost_loans: number;
  overdue_loans: number;
}

function formatDate(dateString: string | null): string {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

function getStatusColor(status: string): string {
  switch (status) {
    case 'active':
      return 'blue';
    case 'returned':
      return 'green';
    case 'overdue':
      return 'red';
    case 'lost':
      return 'gray';
    default:
      return 'gray';
  }
}

interface ExtendModalProps {
  opened: boolean;
  currentDueDate: string | null;
  onClose: () => void;
  onExtend: (newDate: string) => void;
}

function ExtendDueDateModal({
  opened,
  currentDueDate,
  onClose,
  onExtend
}: ExtendModalProps) {
  const [newDate, setNewDate] = useState<string>('');

  const handleExtend = () => {
    if (!newDate) {
      notifications.show({
        title: 'Error',
        message: 'Please select a new due date',
        color: 'red'
      });
      return;
    }
    onExtend(newDate);
    setNewDate('');
  };

  return (
    <Modal opened={opened} onClose={onClose} title='Extend Due Date'>
      <Stack>
        <Text size='sm'>Current due date: {formatDate(currentDueDate)}</Text>
        <TextInput
          type='date'
          label='New Due Date'
          value={newDate}
          onChange={(e) => setNewDate(e.currentTarget.value)}
          required
        />
        <Group justify='flex-end'>
          <Button variant='default' onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleExtend}>Extend</Button>
        </Group>
      </Stack>
    </Modal>
  );
}

export function renderEquipmentLoanManagement(context: InvenTreePluginContext) {
  checkPluginVersion(context);
  return <EquipmentLoanManagement context={context} />;
}

function EquipmentLoanManagement({
  context: _context
}: {
  context?: InvenTreePluginContext;
}) {
  const [loans, setLoans] = useState<Loan[]>([]);
  const [selectedLoan, setSelectedLoan] = useState<LoanDetail | null>(null);
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string | null>('loans');
  const [showReturnModal, setShowReturnModal] = useState(false);
  const [showExtendModal, setShowExtendModal] = useState(false);
  const [returnNotes, setReturnNotes] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 10;

  // Use relative URL that works with any host/port
  const baseUrl = '/api/plugins/equipmentloan';

  // Fetch loans
  const fetchLoans = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.append('status', statusFilter);

      const response = await fetch(`${baseUrl}/loans/list/?${params}`, {
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setLoans(data.results || []);
      } else {
        notifications.show({
          title: 'Error',
          message: 'Failed to fetch loans',
          color: 'red'
        });
      }
    } catch (error) {
      console.error('Error fetching loans:', error);
      notifications.show({
        title: 'Error',
        message: 'Failed to connect to server',
        color: 'red'
      });
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  // Fetch statistics
  const fetchStatistics = useCallback(async () => {
    try {
      const response = await fetch(`${baseUrl}/loans/statistics/`, {
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setStatistics(data);
      }
    } catch (error) {
      console.error('Error fetching statistics:', error);
    }
  }, []);

  // Fetch loan details
  const fetchLoanDetails = useCallback(async (loanId: number) => {
    try {
      const response = await fetch(`${baseUrl}/loans/${loanId}/`, {
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setSelectedLoan(data);
      }
    } catch (error) {
      console.error('Error fetching loan details:', error);
    }
  }, []);

  // Mark loan as returned
  const markAsReturned = useCallback(async () => {
    if (!selectedLoan) return;

    try {
      const response = await fetch(
        `${baseUrl}/loans/${selectedLoan.id}/mark_returned/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          credentials: 'include',
          body: JSON.stringify({ return_notes: returnNotes })
        }
      );

      if (response.ok) {
        notifications.show({
          title: 'Success',
          message: 'Loan marked as returned',
          color: 'green'
        });
        setShowReturnModal(false);
        setReturnNotes('');
        fetchLoans();
        fetchStatistics();
        setSelectedLoan(null);
      } else {
        notifications.show({
          title: 'Error',
          message: 'Failed to mark as returned',
          color: 'red'
        });
      }
    } catch (error) {
      console.error('Error:', error);
      notifications.show({
        title: 'Error',
        message: 'Failed to connect to server',
        color: 'red'
      });
    }
  }, [selectedLoan, returnNotes]);

  // Extend due date
  const extendDueDate = useCallback(
    async (newDate: string) => {
      if (!selectedLoan) return;

      try {
        const response = await fetch(
          `${baseUrl}/loans/${selectedLoan.id}/extend_due_date/`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({ date_due: newDate })
          }
        );

        if (response.ok) {
          notifications.show({
            title: 'Success',
            message: 'Due date extended',
            color: 'green'
          });
          setShowExtendModal(false);
          fetchLoans();
          fetchLoanDetails(selectedLoan.id);
        } else {
          notifications.show({
            title: 'Error',
            message: 'Failed to extend due date',
            color: 'red'
          });
        }
      } catch (error) {
        console.error('Error:', error);
        notifications.show({
          title: 'Error',
          message: 'Failed to connect to server',
          color: 'red'
        });
      }
    },
    [selectedLoan]
  );

  // Initial fetch
  useEffect(() => {
    fetchLoans();
    fetchStatistics();
  }, [fetchLoans, fetchStatistics]);

  // Paginate loans
  const paginatedLoans = loans.slice((page - 1) * pageSize, page * pageSize);

  return (
    <Stack gap='lg' style={{ padding: '20px' }}>
      <Title order={2}>Equipment Loan Management</Title>

      <Tabs value={activeTab} onChange={setActiveTab}>
        <Tabs.List>
          <Tabs.Tab value='loans'>Loans</Tabs.Tab>
          <Tabs.Tab value='statistics'>Statistics</Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value='loans' pt='lg'>
          <Stack gap='lg'>
            {/* Filters */}
            <Group gap='md'>
              <Select
                placeholder='Filter by status'
                data={[
                  { value: '', label: 'All Statuses' },
                  { value: 'active', label: 'Active' },
                  { value: 'returned', label: 'Returned' },
                  { value: 'overdue', label: 'Overdue' },
                  { value: 'lost', label: 'Lost' }
                ]}
                value={statusFilter || ''}
                onChange={(value) => setStatusFilter(value || null)}
                clearable
                searchable
              />
              <Button onClick={fetchLoans} disabled={loading}>
                Refresh
              </Button>
            </Group>

            {/* Loans Table */}
            {loading ? (
              <Center py='xl'>
                <Loader />
              </Center>
            ) : loans.length === 0 ? (
              <Alert title='No loans' color='blue'>
                No equipment loans found. Create a new loan to get started.
              </Alert>
            ) : (
              <>
                <div style={{ overflowX: 'auto' }}>
                  <Table striped highlightOnHover>
                    <Table.Thead>
                      <Table.Tr>
                        <Table.Th>Part Name</Table.Th>
                        <Table.Th>Borrower</Table.Th>
                        <Table.Th>Qty</Table.Th>
                        <Table.Th>Borrowed</Table.Th>
                        <Table.Th>Due Date</Table.Th>
                        <Table.Th>Status</Table.Th>
                        <Table.Th>Days</Table.Th>
                        <Table.Th>Actions</Table.Th>
                      </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>
                      {paginatedLoans.map((loan) => (
                        <Table.Tr key={loan.id}>
                          <Table.Td>{loan.part_name}</Table.Td>
                          <Table.Td>{loan.borrower_username}</Table.Td>
                          <Table.Td>{loan.quantity}</Table.Td>
                          <Table.Td>{formatDate(loan.date_borrowed)}</Table.Td>
                          <Table.Td>{formatDate(loan.date_due)}</Table.Td>
                          <Table.Td>
                            <Badge color={getStatusColor(loan.status)}>
                              {loan.status_display}
                            </Badge>
                          </Table.Td>
                          <Table.Td>{loan.days_borrowed}d</Table.Td>
                          <Table.Td>
                            <Tooltip label='View Details'>
                              <ActionIcon
                                variant='light'
                                onClick={() => {
                                  fetchLoanDetails(loan.id);
                                  setSelectedLoan(loan as LoanDetail);
                                }}
                              >
                                <IconChevronDown size={16} />
                              </ActionIcon>
                            </Tooltip>
                          </Table.Td>
                        </Table.Tr>
                      ))}
                    </Table.Tbody>
                  </Table>
                </div>

                {loans.length > pageSize && (
                  <Group justify='center'>
                    <Pagination
                      value={page}
                      onChange={setPage}
                      total={Math.ceil(loans.length / pageSize)}
                    />
                  </Group>
                )}
              </>
            )}
          </Stack>
        </Tabs.Panel>

        <Tabs.Panel value='statistics' pt='lg'>
          {statistics ? (
            <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }}>
              <Card withBorder>
                <Stack gap='xs'>
                  <Text fw={500} size='sm' color='dimmed'>
                    Total Loans
                  </Text>
                  <Text size='xl' fw={700}>
                    {statistics.total_loans}
                  </Text>
                </Stack>
              </Card>

              <Card withBorder style={{ borderColor: 'blue' }}>
                <Stack gap='xs'>
                  <Text fw={500} size='sm' color='dimmed'>
                    Active Loans
                  </Text>
                  <Text size='xl' fw={700} color='blue'>
                    {statistics.active_loans}
                  </Text>
                </Stack>
              </Card>

              <Card withBorder style={{ borderColor: 'green' }}>
                <Stack gap='xs'>
                  <Text fw={500} size='sm' color='dimmed'>
                    Returned
                  </Text>
                  <Text size='xl' fw={700} color='green'>
                    {statistics.returned_loans}
                  </Text>
                </Stack>
              </Card>

              <Card withBorder style={{ borderColor: 'red' }}>
                <Stack gap='xs'>
                  <Text fw={500} size='sm' color='dimmed'>
                    Overdue
                  </Text>
                  <Text size='xl' fw={700} color='red'>
                    {statistics.overdue_loans}
                  </Text>
                </Stack>
              </Card>

              <Card withBorder style={{ borderColor: 'gray' }}>
                <Stack gap='xs'>
                  <Text fw={500} size='sm' color='dimmed'>
                    Lost
                  </Text>
                  <Text size='xl' fw={700} color='gray'>
                    {statistics.lost_loans}
                  </Text>
                </Stack>
              </Card>
            </SimpleGrid>
          ) : (
            <Center py='xl'>
              <Loader />
            </Center>
          )}
        </Tabs.Panel>
      </Tabs>

      {/* Loan Details Modal */}
      <Modal
        opened={!!selectedLoan}
        onClose={() => {
          setSelectedLoan(null);
          setShowReturnModal(false);
          setShowExtendModal(false);
        }}
        title={`Loan Details: ${selectedLoan?.part_name}`}
        size='lg'
      >
        {selectedLoan && (
          <Stack gap='md'>
            <SimpleGrid cols={2}>
              <div>
                <Text size='sm' color='dimmed'>
                  Borrower
                </Text>
                <Text fw={500}>{selectedLoan.borrower_username}</Text>
              </div>
              <div>
                <Text size='sm' color='dimmed'>
                  Part ID
                </Text>
                <Text fw={500}>{selectedLoan.part_id}</Text>
              </div>
              <div>
                <Text size='sm' color='dimmed'>
                  Quantity
                </Text>
                <Text fw={500}>{selectedLoan.quantity}</Text>
              </div>
              <div>
                <Text size='sm' color='dimmed'>
                  Status
                </Text>
                <Badge color={getStatusColor(selectedLoan.status)}>
                  {selectedLoan.status_display}
                </Badge>
              </div>
              <div>
                <Text size='sm' color='dimmed'>
                  Borrowed
                </Text>
                <Text fw={500}>{formatDate(selectedLoan.date_borrowed)}</Text>
              </div>
              <div>
                <Text size='sm' color='dimmed'>
                  Due
                </Text>
                <Text fw={500}>
                  {formatDate(selectedLoan.date_due)}
                  {selectedLoan.is_overdue && (
                    <>
                      {' '}
                      <Badge color='red' size='xs'>
                        OVERDUE {selectedLoan.days_overdue}d
                      </Badge>
                    </>
                  )}
                </Text>
              </div>
            </SimpleGrid>

            {selectedLoan.notes && (
              <div>
                <Text size='sm' color='dimmed'>
                  Notes
                </Text>
                <Text>{selectedLoan.notes}</Text>
              </div>
            )}

            {selectedLoan.status === 'returned' &&
              selectedLoan.return_notes && (
                <div>
                  <Text size='sm' color='dimmed'>
                    Return Notes
                  </Text>
                  <Text>{selectedLoan.return_notes}</Text>
                </div>
              )}

            {selectedLoan.history && selectedLoan.history.length > 0 && (
              <div>
                <Text fw={500} mb='xs'>
                  History
                </Text>
                <Stack gap='xs' style={{ fontSize: '0.875rem' }}>
                  {selectedLoan.history.map((event) => (
                    <div key={event.id}>
                      <Text color='dimmed' size='xs'>
                        {new Date(event.timestamp).toLocaleDateString()}
                      </Text>
                      <Text>
                        {event.event_type_display} - {event.description}
                      </Text>
                    </div>
                  ))}
                </Stack>
              </div>
            )}

            {selectedLoan.status === 'active' && (
              <Group gap='md'>
                <Button
                  leftSection={<IconCheck size={16} />}
                  onClick={() => setShowReturnModal(true)}
                >
                  Mark as Returned
                </Button>
                <Button
                  variant='light'
                  leftSection={<IconRefresh size={16} />}
                  onClick={() => setShowExtendModal(true)}
                >
                  Extend Due Date
                </Button>
              </Group>
            )}
          </Stack>
        )}
      </Modal>

      {/* Return Equipment Modal */}
      <Modal
        opened={showReturnModal}
        onClose={() => {
          setShowReturnModal(false);
          setReturnNotes('');
        }}
        title='Mark Equipment as Returned'
      >
        <Stack gap='md'>
          <Textarea
            label='Return Notes'
            placeholder='Condition, notes, etc...'
            value={returnNotes}
            onChange={(e) => setReturnNotes(e.currentTarget.value)}
            rows={4}
          />
          <Group justify='flex-end'>
            <Button
              variant='default'
              onClick={() => {
                setShowReturnModal(false);
                setReturnNotes('');
              }}
            >
              Cancel
            </Button>
            <Button onClick={markAsReturned}>Return Equipment</Button>
          </Group>
        </Stack>
      </Modal>

      {/* Extend Due Date Modal */}
      <ExtendDueDateModal
        opened={showExtendModal}
        currentDueDate={selectedLoan?.date_due || null}
        onClose={() => setShowExtendModal(false)}
        onExtend={extendDueDate}
      />
    </Stack>
  );
}
